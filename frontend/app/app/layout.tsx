import TopNav from "@/components/TopNav";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-gray-100">
      <TopNav />
      {children}
    </div>
  );
}
