import { createBrowserRouter, RouterProvider } from "react-router-dom";
import loadable from "@loadable/component";
const Homepage = loadable(() => import("../views/Homepage"));
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

function Redirector({path}: {path: string}) {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/v1')
  })
  return (<></>)
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Redirector path="/v1" />
  },
  {
    path: "/v1",
    element: <Homepage />,
    children: [
    ]
  },

]);