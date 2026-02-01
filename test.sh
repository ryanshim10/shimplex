#!/bin/bash

# Shimplex 테스트 스크립트

echo "🧪 Shimplex 테스트 시작"
echo ""

TEST_PASSED=0
TEST_FAILED=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="http://localhost:8080"

run_test() {
    local name=$1
    local endpoint=$2
    
    echo -n "테스트: $name ... "
    if curl -s "$BASE_URL$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TEST_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((TEST_FAILED++))
    fi
}

echo "1️⃣ 서버 상태 확인"
echo "─────────────────────"
run_test "Health Check" "/api/health"
run_test "Config API" "/api/config"

echo ""
echo "2️⃣ 데이터 API 테스트"
echo "─────────────────────"
run_test "Units API" "/api/units"
run_test "Unit Detail" "/api/units/PINE-201"
run_test "Summary API" "/api/summary/2026-01"

echo ""
echo "3️⃣ 웹 UI 테스트"
echo "─────────────────────"
run_test "Main Page" "/"

echo ""
echo "══════════════════════════"
echo "📊 테스트 결과"
echo "══════════════════════════"
echo -e "통과: ${GREEN}$TEST_PASSED${NC}"
echo -e "실패: ${RED}$TEST_FAILED${NC}"
echo ""

if [ $TEST_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 테스트 통과!${NC}"
    exit 0
else
    echo -e "${RED}⚠️ 일부 테스트 실패${NC}"
    echo "   서버가 실행 중인지 확인: python app.py"
    exit 1
fi
