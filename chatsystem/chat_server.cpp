
#include <iostream>
#include <cstring>
#include <string>

using namespace std;

int main(int argc, char *argv[]) {


    // cout << argv[0] << argv[1] << argv[2] << endl;
    string id = argv[2];
    string cmd = "python run_chat_server.py -id " + id;
    char *command = new char[cmd.length() + 1];
    strcpy(command, cmd.c_str());
    // cout << command << endl;
    system(command);

	return 0;
}
