$api = "http://localhost:8080/api/v1"

Write-Host "Creating KES 1,250 demo payment..."
$payment = Invoke-RestMethod -Method Post -Uri "$api/payment-requests" -ContentType "application/json" -Body (@{
  payerUserId = "USER-DEMO-001"
  merchantId = "MERCHANT-DEMO-001"
  amount = 1250
  currency = "KES"
} | ConvertTo-Json)

$payment | ConvertTo-Json -Depth 5
Write-Host "Authorizing $($payment.id)..."

$approved = Invoke-RestMethod -Method Post -Uri "$api/payment-requests/$($payment.id)/demo-authorize" -ContentType "application/json" -Body (@{
  deviceId = "DEVICE-DEMO-001"
  liveness = $true
} | ConvertTo-Json)

$approved | ConvertTo-Json -Depth 5
Write-Host "Balances:"
Invoke-RestMethod -Uri "$api/wallets/USER-DEMO-001" | ConvertTo-Json
Invoke-RestMethod -Uri "$api/wallets/MERCHANT-DEMO-001" | ConvertTo-Json
