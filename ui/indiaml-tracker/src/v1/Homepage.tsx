import { Outlet, useLocation } from "react-router-dom";
import { TopNav } from "./top-nav";

export default function Component() {
  return (
    <>
      <div className="h-screen w-full relative">
        <TopNav />
        <Outlet />
      </div>
    </>
  );
}
