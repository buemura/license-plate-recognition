export type RecognitionStatus = "NOT_STARTED" | "PENDING" | "COMPLETED" | "FAILED";

export interface RecognitionRequest {
  id: string;
  image_url: string;
  plate_number: string | null;
  status: RecognitionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecognitionSubmitResponse {
  request_id: string;
  status: RecognitionStatus;
  created_at: string;
}

export interface RecognitionListResponse {
  items: RecognitionRequest[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
