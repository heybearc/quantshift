import { getAllReleaseNotes } from '@/lib/release-notes';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ReleaseNotesPage() {
  const releaseNotes = getAllReleaseNotes();

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'major':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'minor':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'patch':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Release Notes
          </h1>
          <p className="text-gray-600">
            Track new features, improvements, and bug fixes in QuantShift
          </p>
        </div>

        {releaseNotes.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-500">No release notes available yet.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {releaseNotes.map((note) => (
              <div
                key={note.version}
                className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
              >
                <div className="bg-gradient-to-r from-gray-50 to-white px-6 py-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h2 className="text-2xl font-bold text-gray-900">
                        v{note.version}
                      </h2>
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getTypeBadgeColor(
                          note.type
                        )}`}
                      >
                        {note.type.charAt(0).toUpperCase() + note.type.slice(1)}
                      </span>
                    </div>
                    <time className="text-sm text-gray-500">
                      {new Date(note.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </time>
                  </div>
                </div>

                <div className="px-6 py-6">
                  <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-li:text-gray-700 prose-strong:text-gray-900">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {note.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
