"use client";

import { useRouter } from "next/navigation";


export default function Home() {
  const router = useRouter();
  const handleSignIn = () => {
    router.push("/signIn");
  }

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <h1>
        This is HomePage
      </h1>
      <button onClick={handleSignIn}>
        login
      </button>

    </div>
  );
}
