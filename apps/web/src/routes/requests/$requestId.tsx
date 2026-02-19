import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { getRecognitionRequest } from "@/api/client";
import { RequestStatus } from "@/components/RequestStatus";

export const Route = createFileRoute("/requests/$requestId")({
  component: RequestDetailPage,
});

function RequestDetailPage() {
  const { requestId } = Route.useParams();

  const { data, isLoading, error } = useQuery({
    queryKey: ["recognition-request", requestId],
    queryFn: () => getRecognitionRequest(requestId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "NOT_STARTED" || status === "PENDING" ? 2000 : false;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-16">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Request Not Found
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          The recognition request you're looking for doesn't exist.
        </p>
        <Link
          to="/"
          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
        >
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <Link
        to="/"
        className="inline-flex items-center text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mb-6"
      >
        <svg
          className="w-4 h-4 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Home
      </Link>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Recognition Request
            </h2>
            <RequestStatus status={data.status} />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Uploaded Image
              </h3>
              <img
                src={data.image_url}
                alt="License plate"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700"
              />
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Request ID</h3>
                <p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all">
                  {data.id}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Recognized Plate
                </h3>
                {data.status === "NOT_STARTED" || data.status === "PENDING" ? (
                  <p className="text-gray-400 dark:text-gray-500 italic">
                    {data.status === "NOT_STARTED" ? "Waiting to process..." : "Processing..."}
                  </p>
                ) : data.plate_number ? (
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {data.plate_number}
                  </p>
                ) : (
                  <p className="text-gray-400 dark:text-gray-500 italic">No plate detected</p>
                )}
              </div>

              {data.error_message && (
                <div>
                  <h3 className="text-sm font-medium text-red-500 dark:text-red-400">Error</h3>
                  <p className="text-sm text-red-600 dark:text-red-400">{data.error_message}</p>
                </div>
              )}

              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</h3>
                <p className="text-sm text-gray-900 dark:text-gray-100">
                  {new Date(data.created_at).toLocaleString()}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Last Updated
                </h3>
                <p className="text-sm text-gray-900 dark:text-gray-100">
                  {new Date(data.updated_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
