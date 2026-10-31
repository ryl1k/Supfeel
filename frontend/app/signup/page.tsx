import type { Metadata } from "next";

import { AuthForm } from "@/components/auth/AuthForm";

export const metadata: Metadata = { title: "Create workspace · Supfeel" };

export default function SignupPage() {
  return <AuthForm mode="signup" />;
}
