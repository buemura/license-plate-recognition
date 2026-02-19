import type {
  RecognitionListResponse,
  RecognitionRequest,
  RecognitionSubmitResponse,
} from "@/types";

const API_BASE = "/api/v1/recognition";

export async function submitRecognitionRequest(
  file: File
): Promise<RecognitionSubmitResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(API_BASE, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to submit recognition request");
  }

  return response.json();
}

export async function getRecognitionRequest(
  requestId: string
): Promise<RecognitionRequest> {
  const response = await fetch(`${API_BASE}/${requestId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Recognition request not found");
    }
    throw new Error("Failed to fetch recognition request");
  }

  return response.json();
}

export async function listRecognitionRequests(
  page: number = 1,
  pageSize: number = 10
): Promise<RecognitionListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const response = await fetch(`${API_BASE}?${params}`);

  if (!response.ok) {
    throw new Error("Failed to fetch recognition requests");
  }

  return response.json();
}
