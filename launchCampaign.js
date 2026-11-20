// Switch mode to "live" only after a shared enrollment API returns verified counts.
export const launchCampaign = {
  mode: "demo",
  capacity: 100,
  demoClaimed: 78,
  plannedRegularPriceINR: 4999,
  enrollmentEndpoint: null,
  activityEndpoint: null,
  sampleActivity: [
    { name: "Rohan", city: "Hyderabad", seat: 79, minutesAgo: 2 },
    { name: "Aisha", city: "Bengaluru", seat: 80, minutesAgo: 4 },
    { name: "Neha", city: "Pune", seat: 81, minutesAgo: 6 },
    { name: "Arjun", city: "Chennai", seat: 82, minutesAgo: 9 }
  ]
};
export async function submitEnrollment(entry) {
  if (launchCampaign.mode === "demo") {
    return { mode: "demo", accepted: true };
  }
  if (!launchCampaign.enrollmentEndpoint) {
    throw new Error("Live enrollment is not configured yet.");
  }
  const response = await fetch(launchCampaign.enrollmentEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry)
  });
  if (!response.ok) throw new Error("We could not reserve your seat. Please try again.");
  const result = await response.json();
  if (!result || result.accepted !== true || !Number.isInteger(result.claimed)) {
    throw new Error("Enrollment response was incomplete.");
  }
  return result;
}
