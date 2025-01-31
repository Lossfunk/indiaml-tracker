import { Outlet, useLocation } from "react-router-dom";

export default function Component() {
  return (
    <>
      <div className="h-screen w-full relative">
        hi
        <Outlet />
      </div>
    </>
  );
}
