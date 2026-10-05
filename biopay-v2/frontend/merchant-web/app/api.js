const API = process.env.NEXT_PUBLIC_PAYMENT_API_URL || "http://localhost:8080";

export async function request(path, body) {
  let response;
  try {
    response = await fetch(`${API}/api/v1${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(15000)
    });
  } catch {
    throw new Error("Cannot reach the payment API. Check that it is running and try again.");
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error("The payment API returned an unreadable response. Try again."); }
  if (!response.ok) throw new Error(data.error || "The request failed. Try again.");
  return data;
}
