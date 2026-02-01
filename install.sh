#!/bin/bash

# Shimplex 설치 스크립트
# 어떤 컴퓨터에서든 Python만 있으면 실행 가능

set -e

echo "🚀 Shimplex 설치 시작..."
echo ""

# Python 버전 확인
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.8"

if [ -z "$PYTHON_VERSION" ]; then
    echo "❌ Python 3이 설치되어 있지 않습니다."
    echo "   설치 방법: https://www.python.org/downloads/"
    exit 1
fi

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ Python $REQUIRED_VERSION 이상이 필요합니다. (현재: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION 확인"

# 가상환경 생성 (선택)
if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔄 가상환경 활성화..."
source venv/bin/activate

# 패키지 설치
echo "📥 필요한 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ 설치 완료!"
echo ""
echo "🎉 Shimplex를 시작하려면:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🔗 브라우저에서 http://localhost:8080 접속"
echo ""
echo "⚙️ 처음 설정:"
echo "   1. 설정 탭에서 LLM API 키 입력 (OpenAI/Claude)"
echo "   2. 또는 Ollama 선택해서 로컬 AI 사용"
echo ""
