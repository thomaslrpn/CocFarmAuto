import logo from "../assets/logo.png";

/** Logo de CoC AutoFarm (même dessin que l'icône de l'application : desktop/branding/icon.svg). */
export function AppLogo({ className = "size-6" }: { className?: string }) {
  return <img src={logo} alt="" aria-hidden className={`shrink-0 ${className}`} />;
}
