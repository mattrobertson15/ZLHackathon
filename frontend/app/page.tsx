import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="w-full h-screen flex flex-col items-center justify-center bg-white">
      <div className="flex flex-col items-center gap-8">
        <Image
          src="/safety_sentinel_logo.png"
          alt="Safety Sentinel Logo"
          width={300}
          height={300}
          priority
        />
        <Link
          href="/app/dashboard"
          className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          Enter App
        </Link>
      </div>
    </div>
  );
}
