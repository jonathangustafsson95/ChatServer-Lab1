// Client.c : Defines the entry point for the console application.
//input from client with the letters(ä,å,ö) is not supported

#include "stdafx.h"
#include <winsock2.h>
#include <Ws2tcpip.h>
#include "simpio.h"
#include "strlib.h"
#include<time.h>
#include<stdio.h>
#include<sys/types.h>



#pragma comment(lib, "Ws2_32.lib")
// This function delays recieving from server with 1 second.
void delay(int number)
{
	int milliseconds = 1000 * number;
	clock_t start_time = clock();
	while (clock() < start_time + milliseconds)
		;
}

int _tmain(int argc, _TCHAR * argv[])
{
	// Initiate WinSock
	WORD wVersionRequested;
	WSADATA wsaData;
	int err;
	wVersionRequested = MAKEWORD(2, 2);
	err = WSAStartup(wVersionRequested, &wsaData);

	// create a socket
	SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

	// Get address information 
	struct addrinfo* info;
	int ok = getaddrinfo("10.10.170.243", "12373", NULL, &info);
	if (ok != 0) {
		WCHAR* error = gai_strerror(ok);
		printf("%s\n", error);
	}
	else while (info->ai_family != AF_INET && info->ai_next != NULL)
		info = info->ai_next;

	ok = connect(s, info->ai_addr, info->ai_addrlen);
	// connect socket to the address
	int iResult;
	char buffer1[1024];

	iResult = recv(s, buffer1, 1024, 0);
	if (iResult > 0) {
		fwrite(buffer1, 1, iResult, stdout);

	}

	while (TRUE)
	{
		// send a command to server
		while (TRUE)
		{
			string input = GetLine();
			string command = Concat(ConvertToUpperCase(SubString(input, 0, 3)), ":");
			string message = SubString(input, 5, strlen(input));
			string finalmessage = Concat(command, message);
			int arguments = 1;
			int i;

			//counts number of arguments in input
			for (i = 4; i <= strlen(finalmessage); i++)
			{
				if (finalmessage[i] == ' ' || finalmessage[i] == ':')
				{
					arguments++;
				}
			}
			if (StringCompare(command, "QUIT:") == 0)
			{
				ok = send(s, finalmessage, strlen(finalmessage), 0);
				
				break;
			}
			else if (StringCompare(command, ":") == 0)
			{
				finalmessage = "NOOP:NOOP";
				ok = send(s, finalmessage, strlen(finalmessage), 0);
				break;
			}
			else if (StringCompare(command, "NICK:") == 0 && arguments == 2)
			{
				ok = send(s, finalmessage, strlen(finalmessage), 0);
				break;
			}
			else if (StringCompare(command, "JOIN:") == 0 && arguments == 2)
			{
				ok = send(s, finalmessage, strlen(finalmessage), 0);
				break;
			}
			else if (StringCompare(command, "PART:") == 0 && arguments == 2)
			{

				ok = send(s, finalmessage, strlen(finalmessage), 0);
				break;
			}
			else if (StringCompare(command, "LIST:") == 0 && arguments == 2)
			{
				ok = send(s, finalmessage, strlen(finalmessage), 0);
				break;
			}
			else if (StringCompare(command, "KICK:") == 0)
			{
				int index = 0;
				for (int i = 0; i < strlen(finalmessage); i++) // change the input into a correct format to send finalmessage to server
				{
					if (finalmessage[i] == ' ')
					{
						index++;
						if (index == 2) //control if finalmessage has correct amount of arguments
						{
							finalmessage[i] = ':';
							finalmessage[4] = ' ';
							ok = send(s, finalmessage, strlen(finalmessage), 0);
							break;
						}
					}
				} if (index != 2)
				{
					printf("Not the right amount of arguments\n");
					continue;
				}
				if (index == 2); {break; }
			}
			else if (StringCompare(command, "SEND:") == 0)
			{
				int index = 0;
				for (int i = 0; i < strlen(finalmessage); i++) // change the input into a correct format to send finalmessage to server
				{
					if (finalmessage[i] == ' ')
					{
						index++;
						if (index == 1) //control if finalmessage has correct amount of arguments
						{
							finalmessage[i] = ':';
							finalmessage[4] = ' ';
							ok = send(s, finalmessage, strlen(finalmessage), 0);
							break;
						}
					}
				} if (index != 1)
				{
					printf("Not the right amount of arguments\n");
					continue;
				}
				if (index == 1); {break; }
			}
			else
			{
				printf("Theres no such command or you did not enter the right amount of arguments\n");
			}

		}
		delay(1); // a pause so all other clients can catch up
		// print data from server
		while (TRUE)
		{
			int iResult;
			char* buffer = (char*)malloc(1042 * sizeof(char*));
			do {
				iResult = recv(s, buffer, 1024, 0);
				if (iResult > 0 && buffer > 0) {
					fwrite(buffer, 1, iResult, stdout);

				}
				// The only time iResult is 5 is when the server sends "QUIT\n"
				if (iResult == 5)
				{
					printf("Disconnected from server...");
					closesocket(s);
					WSACleanup();
					return 0;
				}
				free(buffer);

				break;
			} while (iResult > 0 && buffer > 0);
			fflush(stdout);
			break;
		}

	}

}