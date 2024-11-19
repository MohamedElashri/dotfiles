# Add this to your .bashrc or .zshrc
busywork() {
    local descriptions=(
        "Monitoring processes and managing memory usage..."
        "Scanning system logs for critical issues..."
        "Running inference benchmark on CPU and GPU, comparing results..."
        "Checking data integrity and creating backups..."
        "Analyzing system resource usage and providing optimization tips..."
    )

    local variations=(
        # 1. Continuous Process Monitoring and Management
        'while true; do \
            echo "$(date): Checking running processes..."; sleep 1; \
            ps aux --sort=-%mem | head -n 5; sleep 1; \
            echo "$(date): Monitoring high-memory processes..."; sleep 1; \
            ps aux --sort=-%mem | awk "{if (\$4 > 30) print}" | head -n 2; sleep 2; \
            echo "$(date): Attempting resource adjustments..."; sleep 1; \
            echo "PID 1234 (example_process) marked for resource reduction"; sleep 1; \
            echo "$(date): Reviewing CPU usage..."; sleep 1; \
            ps aux --sort=-%cpu | head -n 5; sleep 2; \
        done'

        # 2. Continuous Log Scanning with Realistic Output
        'while true; do \
            echo "$(date): Starting log scan..."; sleep 1; \
            tail -f /var/log/syslog /var/log/auth.log 2>/dev/null | grep -E "ERROR|WARNING|Failed|Accepted|Denied" | while read line; do \
                echo "$line"; sleep 0.5; \
                echo "$(date): Checking recent entries..."; sleep 1; \
            done; \
            echo "$(date): No immediate critical issues detected. Continuing scan..."; sleep 2; \
        done'

        # 3. Continuous Inference Benchmark on CPU vs GPU with Throughput Checks
        'while true; do \
            echo "$(date): Loading dataset for inference..."; sleep 2; \
            echo "$(date): Running CPU inference benchmark..."; sleep 3; \
            echo "CPU Inference: Throughput at 175 samples/sec"; sleep 2; \
            echo "Accuracy: 82.5%"; sleep 1; \
            echo "$(date): Switching to GPU inference benchmark..."; sleep 2; \
            echo "$(date): GPU inference in progress, checking throughput..."; sleep 1; \
            echo "GPU Inference: Throughput at 476 samples/sec"; sleep 2; \
            echo "Accuracy: 83.0%"; sleep 2; \
            echo "$(date): Benchmark comparison: GPU is 2.7x faster, Accuracy +0.5%"; sleep 2; \
            echo "$(date): Re-running GPU inference to verify consistency..."; sleep 2; \
        done'

        # 4. Continuous Data Integrity Check and Backup Simulation
        'while true; do \
            echo "$(date): Starting data integrity check on ~/inference_engine..."; sleep 2; \
            ls -lh ~/inference_engine 2>/dev/null | head -n 5; sleep 1; \
            echo "$(date): Verifying integrity of critical files..."; sleep 1; \
            ls -lh ~/inference_engine/important_file.dat 2>/dev/null || echo "File missing! Check configuration."; sleep 1; \
            echo "$(date): No corruption found. Preparing backup..."; sleep 1; \
            echo "Backing up to /backup/inference_engine"; sleep 3; \
            ls -lh /backup/inference_engine 2>/dev/null | head -n 5; sleep 1; \
            echo "$(date): Backup verification complete."; sleep 2; \
        done'

        # 5. Continuous System Resource Analysis with Usage Monitoring
        'while true; do \
            echo "$(date): Collecting CPU and memory usage data..."; sleep 1; \
            top -bn1 | head -n 10; sleep 2; \
            echo "$(date): Checking memory usage trends..."; sleep 1; \
            free -h | grep -E "Mem|Swap"; sleep 1; \
            echo "$(date): CPU load distribution across cores..."; sleep 1; \
            mpstat -P ALL 1 1 | tail -n +4; sleep 2; \
            echo "$(date): System usage check complete."; sleep 2; \
        done'
    )

    # Randomly select a description and corresponding command
    local index=$((RANDOM % ${#variations[@]}))
    local selected_description="${descriptions[$index]}"
    local selected_variation="${variations[$index]}"
    
    # Print the brief description in green
    echo -e "\033[0;32m$selected_description\033[0m"
    
    # Execute the selected command
    eval "$selected_variation"
}

# Alias to appear busy
alias abusy="busywork"
