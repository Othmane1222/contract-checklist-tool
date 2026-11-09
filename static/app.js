const form = document.getElementById("upload-form");
const statusText = document.getElementById("status");
const output = document.getElementById("output");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusText.textContent = "Checking the contract… this can take up to a minute.";
  output.textContent = "";

  try {
    const response = await fetch("/api/check", {
      method: "POST",
      body: new FormData(form),
    });
    const data = await response.json();

    if (!response.ok) {
      statusText.textContent = data.detail || "Something went wrong.";
      return;
    }

    statusText.textContent = `Checked ${data.results.length} items.`;
    output.textContent = JSON.stringify(data, null, 2);
  } catch {
    statusText.textContent = "Could not reach the server.";
  }
});