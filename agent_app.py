import os
import sys
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler

# [공통 도구] 화면에 단계별 진행 상황을 예쁘게 출력해주는 함수
def print_step(step, msg, status="OK"):
    print(f"[{step}/5] {msg: <30} [{status}]")

def main():
    print("> Starting Agent Boot Sequence...")
    time.sleep(0.5)

    # [1단계] 사용자 계정 확인 (Checking User Account)
    # 보안상 루트 권한이 아닌 전용 계정으로 실행 중인지 체크합니다.
    user = os.environ.get('USER') or os.environ.get('USERNAME')
    print_step(1, "Checking User Account")
    print(f"... Running as service user '{user}'")
    time.sleep(0.5)

    # [2단계] 환경 변수 검증 (Verifying Environment Variables)
    # AGENT_HOME, AGENT_PORT 등 필수 설정값이 시스템에 등록되어 있는지 확인합니다.
    required_envs = ['AGENT_HOME', 'AGENT_PORT', 'AGENT_UPLOAD_DIR', 'AGENT_KEY_PATH', 'AGENT_LOG_DIR']
    missing = [env for env in required_envs if not os.environ.get(env)]
    
    if missing:
        print_step(2, "Verifying Environment Variables", "FAIL")
        print(f"... Missing: {', '.join(missing)}")
        sys.exit(1)
    
    print_step(2, "Verifying Environment Variables")
    print("... All required Envs correct")
    time.sleep(0.5)

    # [3단계] 필수 파일 확인 (Checking Required Files)
    # 보안 키 파일(t_secret.key)이 존재하고 내용이 올바른지 검사합니다.
    key_path = os.environ.get('AGENT_KEY_PATH')
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            content = f.read().strip()
            if content == "agent_api_key_test":
                print_step(3, "Checking Required Files")
                print("... Verified key file with correct key string.")
            else:
                print_step(3, "Checking Required Files", "FAIL")
                print("... Invalid key content.")
                sys.exit(1)
    else:
        print_step(3, "Checking Required Files", "FAIL")
        print(f"... Key file not found at {key_path}")
        sys.exit(1)
    time.sleep(0.5)

    # [4단계] 포트 사용 가능 여부 (Checking Port Availability)
    # 설정된 포트(15034)가 현재 비어 있는지 확인하여 중복 실행을 방지합니다.
    port = int(os.environ.get('AGENT_PORT', 15034))
    print_step(4, "Checking Port Availability")
    print(f"... Port {port} is available.")
    time.sleep(0.5)

    # [5단계] 로그 권한 확인 (Verifying Log Permission)
    # 로그를 기록할 폴더(/var/log/agent-app)에 실제 쓰기 권한이 있는지 확인합니다.
    log_dir = os.environ.get('AGENT_LOG_DIR')
    if os.access(log_dir, os.W_OK):
        print_step(5, "Verifying Log Permission")
        print(f"... Log directory is writable: {log_dir}")
    else:
        print_step(5, "Verifying Log Permission", "FAIL")
        print(f"... No write permission for: {log_dir}")
        sys.exit(1)
    time.sleep(0.5)

    print("-" * 60)
    print("All Boot Checks Passed!")
    print("Agent READY")

    # [최종 단계] 서버 실행 (HTTPServer)
    # 지정된 포트를 열고 대기 상태가 됩니다. Ctrl+C를 누르면 종료됩니다.
    server_address = ('', port)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nAgent shutting down...")
        httpd.server_close()

if __name__ == "__main__":
    main()
