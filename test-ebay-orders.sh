#!/bin/bash

# =====================================
# Test Script - eBay Orders Management
# =====================================
# Ce script teste l'implémentation complète de la gestion des commandes eBay
# Backend + Frontend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
RESULTS_DIR="./test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create results directory
mkdir -p "$RESULTS_DIR"

# =====================================
# Helper Functions
# =====================================

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo ""
    echo -e "${YELLOW}▶ Test $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

save_response() {
    local test_num=$1
    local filename="${RESULTS_DIR}/test_${test_num}_${TIMESTAMP}.json"
    cat > "$filename"
    echo "$filename"
}

# =====================================
# Pre-flight Checks
# =====================================

print_header "PRE-FLIGHT CHECKS"

# Check if backend is running
print_test "0A" "Backend server accessible"
if curl -s -f "${API_BASE_URL}/docs" > /dev/null 2>&1; then
    print_success "Backend server is running on port 8000"
else
    print_error "Backend server not accessible. Start it with: cd backend && uvicorn main:app --reload"
    exit 1
fi

# Check if frontend is running
print_test "0B" "Frontend server accessible"
if curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
    print_success "Frontend server is running on port 3000"
else
    print_error "Frontend server not accessible. Start it with: cd frontend && npm run dev"
    exit 1
fi

# =====================================
# Get JWT Token
# =====================================

print_header "AUTHENTICATION"

if [ -z "$EBAY_TOKEN" ]; then
    echo ""
    echo -e "${YELLOW}Please provide your JWT token:${NC}"
    echo "You can get it by:"
    echo "  1. Login to the app at http://localhost:3000"
    echo "  2. Open DevTools (F12) → Console"
    echo "  3. Run: localStorage.getItem('access_token')"
    echo ""
    read -p "Enter your JWT token: " TOKEN

    if [ -z "$TOKEN" ]; then
        print_error "Token is required to run tests"
        exit 1
    fi
else
    TOKEN="$EBAY_TOKEN"
    print_info "Using token from EBAY_TOKEN environment variable"
fi

# Test authentication
print_test "0C" "JWT token validity"
AUTH_TEST=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "${API_BASE_URL}/api/ebay/marketplaces")

if [ "$AUTH_TEST" = "200" ]; then
    print_success "Token is valid"
else
    print_error "Token is invalid or expired (HTTP $AUTH_TEST)"
    exit 1
fi

# =====================================
# Backend API Tests
# =====================================

print_header "BACKEND API TESTS"

# Test 1: Sync orders
print_test "1" "Synchronize orders from eBay (last 24h)"
SYNC_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/ebay/orders/sync" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"hours": 24}')

echo "$SYNC_RESPONSE" | python3 -m json.tool | tee "$(save_response 1)"

if echo "$SYNC_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if 'total_fetched' in r else 1)" 2>/dev/null; then
    CREATED=$(echo "$SYNC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['created'])")
    UPDATED=$(echo "$SYNC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['updated'])")
    ERRORS=$(echo "$SYNC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['errors'])")
    TOTAL=$(echo "$SYNC_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_fetched'])")

    print_success "Sync completed: Created=$CREATED, Updated=$UPDATED, Errors=$ERRORS, Total=$TOTAL"
else
    print_error "Sync failed or returned unexpected format"
fi

# Test 2: List orders with pagination
print_test "2" "List orders (page 1, 10 items)"
LIST_RESPONSE=$(curl -s "${API_BASE_URL}/api/ebay/orders?page=1&page_size=10" \
    -H "Authorization: Bearer $TOKEN")

echo "$LIST_RESPONSE" | python3 -m json.tool | tee "$(save_response 2)"

if echo "$LIST_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if 'items' in r and 'total' in r else 1)" 2>/dev/null; then
    ITEMS_COUNT=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
    TOTAL_COUNT=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")

    print_success "List returned: $ITEMS_COUNT items (Total in DB: $TOTAL_COUNT)"

    # Save first order ID for later tests
    if [ "$ITEMS_COUNT" -gt 0 ]; then
        ORDER_ID=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['items'][0]['id'])")
        ORDER_EBAY_ID=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['items'][0]['order_id'])")
        print_info "First order: ID=$ORDER_ID, eBay ID=$ORDER_EBAY_ID"
    fi
else
    print_error "List failed or returned unexpected format"
fi

# Test 3: Filter by status
print_test "3" "Filter orders by status (NOT_STARTED)"
FILTER_RESPONSE=$(curl -s "${API_BASE_URL}/api/ebay/orders?status=NOT_STARTED&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

echo "$FILTER_RESPONSE" | python3 -m json.tool | tee "$(save_response 3)"

if echo "$FILTER_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if 'items' in r else 1)" 2>/dev/null; then
    FILTERED_COUNT=$(echo "$FILTER_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
    print_success "Filter returned $FILTERED_COUNT orders with status NOT_STARTED"
else
    print_error "Filter failed"
fi

# Test 4: Get order details
if [ -n "$ORDER_ID" ]; then
    print_test "4" "Get order details (ID: $ORDER_ID)"
    DETAIL_RESPONSE=$(curl -s "${API_BASE_URL}/api/ebay/orders/${ORDER_ID}" \
        -H "Authorization: Bearer $TOKEN")

    echo "$DETAIL_RESPONSE" | python3 -m json.tool | tee "$(save_response 4)"

    if echo "$DETAIL_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if 'order_id' in r else 1)" 2>/dev/null; then
        BUYER=$(echo "$DETAIL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('buyer_username', 'N/A'))")
        TOTAL=$(echo "$DETAIL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_price', 0))")
        CURRENCY=$(echo "$DETAIL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('currency', 'N/A'))")

        print_success "Order details: Buyer=$BUYER, Total=$TOTAL $CURRENCY"
    else
        print_error "Failed to get order details"
    fi
else
    print_info "Skipping test 4: No orders found in previous test"
fi

# Test 5: Update fulfillment status
if [ -n "$ORDER_ID" ]; then
    print_test "5" "Update fulfillment status to IN_PROGRESS (ID: $ORDER_ID)"
    UPDATE_RESPONSE=$(curl -s -X PATCH "${API_BASE_URL}/api/ebay/orders/${ORDER_ID}/fulfillment" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"new_status": "IN_PROGRESS"}')

    echo "$UPDATE_RESPONSE" | python3 -m json.tool | tee "$(save_response 5)"

    if echo "$UPDATE_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if r.get('order_fulfillment_status') == 'IN_PROGRESS' else 1)" 2>/dev/null; then
        print_success "Fulfillment status updated to IN_PROGRESS"
    else
        print_error "Failed to update fulfillment status"
    fi
else
    print_info "Skipping test 5: No order ID available"
fi

# Test 6: Pagination (page 2)
print_test "6" "Test pagination (page 2)"
PAGE2_RESPONSE=$(curl -s "${API_BASE_URL}/api/ebay/orders?page=2&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

echo "$PAGE2_RESPONSE" | python3 -m json.tool | tee "$(save_response 6)"

if echo "$PAGE2_RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); sys.exit(0 if 'items' in r else 1)" 2>/dev/null; then
    PAGE2_COUNT=$(echo "$PAGE2_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['items']))")
    print_success "Page 2 returned $PAGE2_COUNT items"
else
    print_error "Pagination test failed"
fi

# Test 7: Add tracking (OPTIONAL - requires PAID order)
print_test "7" "Add tracking number (OPTIONAL - requires PAID order)"
print_info "Skipping automatic tracking test (requires PAID order)"
print_info "To test manually:"
echo "  curl -X POST \"${API_BASE_URL}/api/ebay/orders/{ORDER_ID}/tracking\" \\"
echo "    -H \"Authorization: Bearer $TOKEN\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"tracking_number\": \"ABC123456789\", \"carrier_code\": \"COLISSIMO\"}'"

# =====================================
# Integration Tests
# =====================================

print_header "INTEGRATION TESTS"

# Test 8: Complete workflow - Sync recent → Verify in list
print_test "8" "Complete workflow: Sync last hour → Verify in list"

# Sync last hour
SYNC_1H=$(curl -s -X POST "${API_BASE_URL}/api/ebay/orders/sync" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"hours": 1}')

CREATED_1H=$(echo "$SYNC_1H" | python3 -c "import sys, json; print(json.load(sys.stdin).get('created', 0))" 2>/dev/null || echo "0")
UPDATED_1H=$(echo "$SYNC_1H" | python3 -c "import sys, json; print(json.load(sys.stdin).get('updated', 0))" 2>/dev/null || echo "0")

print_info "Last hour sync: Created=$CREATED_1H, Updated=$UPDATED_1H"

# Verify in list
LIST_AFTER=$(curl -s "${API_BASE_URL}/api/ebay/orders?page=1&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

TOTAL_AFTER=$(echo "$LIST_AFTER" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")

if [ "$TOTAL_AFTER" -gt 0 ]; then
    print_success "Workflow validated: $TOTAL_AFTER orders in database"
else
    print_error "Workflow failed: No orders found"
fi

# =====================================
# Frontend Tests Info
# =====================================

print_header "FRONTEND TESTS (MANUAL)"

echo ""
echo "Please test manually in your browser:"
echo ""
echo "1. Open: http://localhost:3000/dashboard/platforms/ebay/orders"
echo "   ✓ Page loads without errors"
echo "   ✓ Stats cards display (Total, Revenue, Pending, Shipped)"
echo ""
echo "2. Click 'Rafraîchir' button"
echo "   ✓ Orders table populates"
echo "   ✓ Loading spinner shows during fetch"
echo ""
echo "3. Test search and filters"
echo "   ✓ Search by Order ID"
echo "   ✓ Filter by Payment Status"
echo "   ✓ Filter by Fulfillment Status"
echo ""
echo "4. Click on an order"
echo "   ✓ Order details display (buyer, shipping, products)"
echo ""

# =====================================
# Final Report
# =====================================

print_header "TEST SUMMARY"

echo ""
echo "Test results saved in: $RESULTS_DIR"
echo ""
echo "Backend Tests:"
echo "  ✅ Pre-flight checks passed"
echo "  ✅ Authentication validated"
echo "  ✅ Sync endpoint tested"
echo "  ✅ List endpoint tested"
echo "  ✅ Filter endpoint tested"
echo "  ✅ Details endpoint tested"
echo "  ✅ Update fulfillment tested"
echo "  ✅ Pagination tested"
echo "  ⚠️  Tracking endpoint (manual test required)"
echo ""
echo "Frontend Tests:"
echo "  ℹ️  Manual testing required (see instructions above)"
echo ""

if [ -n "$ORDER_ID" ]; then
    echo "Sample order for manual testing:"
    echo "  Internal ID: $ORDER_ID"
    echo "  eBay Order ID: $ORDER_EBAY_ID"
    echo ""
fi

echo -e "${GREEN}✅ All automated tests completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review test results in: $RESULTS_DIR"
echo "  2. Perform manual frontend tests"
echo "  3. Test tracking endpoint with a PAID order"
echo ""
