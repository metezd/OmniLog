"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AuthBanner from "@/components/auth/AuthBanner";
import { register } from "@/lib/services/auth";

export default function RegisterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await register({ username, email, password });
      
      // Kayıt başarılı olduktan sonra login sayfasına yönlendir
      router.push("/login?registered=true");
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      
      if (typeof errorDetail === "object" && errorDetail !== null) {
        setError(errorDetail[0]?.msg || JSON.stringify(errorDetail));
      } else {
        setError(errorDetail || "Kayıt olurken bir hata oluştu.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <AuthBanner variant="error">{error}</AuthBanner>}
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1.5">Kullanıcı Adı</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan"
          placeholder="kullaniciadi"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1.5">E-posta</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan"
          placeholder="ornek@bilgiedu.net"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1.5">Şifre</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded-xl bg-black/50 border border-white/10 px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-horizon-cyan"
          placeholder="••••••••"
        />
      </div>
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-xl bg-horizon-crimson/20 hover:bg-horizon-crimson/30 border border-horizon-crimson/40 py-2.5 text-xs font-medium text-rose-200 transition-all disabled:opacity-50"
      >
        {isLoading ? "Hesap oluşturuluyor..." : "Kayıt Ol"}
      </button>
    </form>
  );
}