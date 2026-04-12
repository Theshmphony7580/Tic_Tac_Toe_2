import Sidebar from "@/app/components/sidebar/page";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen relative">
      {/* Top navbar placeholder (matches 4rem / 16 spacing referenced in Sidebar) */}
      <header className="h-10 border-b border-gray-200 bg-white flex items-center px-6 fixed top-0 w-full z-50">
        <h1 className="font-semibold text-lg">SEO Platform</h1>
      </header>

      {/* Main content layout */}
      <div className="flex pt-10 h-screen">
        <Sidebar />

        {/* Main padding accounts for the collapsed sidebar width (64px) */}
        <main className="flex-1 w-full pl-[64px] overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
