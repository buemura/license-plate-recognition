import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ImageUpload } from "@/components/ImageUpload";
import { RequestList } from "@/components/RequestList";
import { listRecognitionRequests } from "@/api/client";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["recognition-requests"],
    queryFn: () => listRecognitionRequests(1, 20),
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          Upload License Plate Image
        </h2>
        <ImageUpload onSuccess={() => refetch()} />
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          Recognition Requests
        </h2>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No recognition requests yet. Upload an image to get started.
          </div>
        ) : (
          <RequestList requests={data?.items || []} />
        )}
      </section>
    </div>
  );
}
