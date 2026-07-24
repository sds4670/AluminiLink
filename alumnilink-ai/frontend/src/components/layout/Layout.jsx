import { useState } from "react";
import Sidebar from "./Sidebar";
import TopNav from "./TopNav";

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-50">
      <div className={`flex flex-shrink-0 overflow-hidden transition-all duration-300 ${sidebarOpen ? "w-64" : "w-0"}`}>
        <Sidebar />
      </div>
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopNav sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen((o) => !o)} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
