#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <time.h>

#define TARGETS_FILE "targets.txt"
#define LOG_FILE "downtime_log.txt"

void log_event(const char* target, const char* status) {
    FILE *log = fopen(LOG_FILE, "a");
    if (!log) return;
    
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    char time_str[64];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm);
    
    printf("[%s] %s: %s\n", time_str, status, target);
    fprintf(log, "[%s] %s: %s\n", time_str, status, target);
    fclose(log);
}

int ping_target(const char* target) {
    char command[256];
    // -n 1 (send 1 packet), -w 1000 (1000ms timeout), suppress output
    snprintf(command, sizeof(command), "ping -n 1 -w 1000 %s > nul 2>&1", target);
    return (system(command) == 0);
}

DWORD WINAPI monitor_target(LPVOID lpParam) {
    char* target = (char*)lpParam;
    int was_down = 0;
    printf("Started monitoring: %s\n", target);
    
    while (1) {
        int is_up = ping_target(target);
        if (!is_up && !was_down) {
            log_event(target, "DOWN");
            was_down = 1;
        } else if (is_up && was_down) {
            log_event(target, "RESTORED");
            was_down = 0;
        }
        Sleep(3000); // 3-second interval
    }
    return 0;
}

int main() {
    printf("=== Portable Ping Monitor (WinXP Compatible) ===\n");
    FILE *f = fopen(TARGETS_FILE, "r");
    if (!f) {
        f = fopen(TARGETS_FILE, "w");
        fprintf(f, "8.8.8.8\n1.1.1.1\n");
        fclose(f);
        printf("Created '%s'. Please add IPs and restart.\n", TARGETS_FILE);
        system("pause");
        return 1;
    }

    char line[256];
    int count = 0;
    while (fgets(line, sizeof(line), f)) {
        line[strcspn(line, "\r\n")] = 0; // Remove newline
        if (strlen(line) > 0) {
            char* t = malloc(strlen(line) + 1);
            strcpy(t, line);
            CreateThread(NULL, 0, monitor_target, t, 0, NULL);
            count++;
        }
    }
    fclose(f);

    if (count == 0) {
        printf("No targets found.\n");
        system("pause");
        return 1;
    }
    
    printf("Loaded %d targets. Close the window to stop.\n\n", count);
    while(1) Sleep(1000); // Keep main thread alive
    return 0;
}