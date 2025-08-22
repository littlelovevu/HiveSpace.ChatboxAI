from agents.tools.image_tool import _select_order_by_prompt

# Test order selection
order = _select_order_by_prompt('ORD-2024-001')
if order:
    print(f"Order ID: {order['order_id']}")
    print(f"Customer: {order['customer_name']}")
    print(f"Items: {[item['name'] for item in order['items']][:2]}")
    print(f"Total: {order['total_amount']:,} VNĐ")
else:
    print("No order found")
