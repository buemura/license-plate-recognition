import { Link } from "@tanstack/react-router";
import type { RecognitionRequest } from "@/types";
import { RequestStatus } from "./RequestStatus";

interface RequestListProps {
  requests: RecognitionRequest[];
}

export function RequestList({ requests }: RequestListProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Image
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Plate Number
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Created
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {requests.map((request) => (
            <tr key={request.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
              <td className="px-6 py-4 whitespace-nowrap">
                <img
                  src={request.image_url}
                  alt="License plate"
                  className="h-12 w-auto rounded"
                />
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {request.status === "NOT_STARTED" || request.status === "PENDING" ? (
                  <span className="text-gray-400 dark:text-gray-500 italic">
                    {request.status === "NOT_STARTED" ? "Waiting..." : "Processing..."}
                  </span>
                ) : request.plate_number ? (
                  <span className="font-mono font-semibold text-gray-900 dark:text-white">
                    {request.plate_number}
                  </span>
                ) : (
                  <span className="text-gray-400 dark:text-gray-500 italic">No plate detected</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <RequestStatus status={request.status} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {new Date(request.created_at).toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                <Link
                  to="/requests/$requestId"
                  params={{ requestId: request.id }}
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                >
                  View Details
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
