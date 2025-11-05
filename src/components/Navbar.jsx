import { Link } from "react-router-dom";

export default function NavBar() {
  return (
    <nav style={{ padding: 12, borderBottom: "1px solid #eee" }}>
      <Link to="/client/dashboard">Dashboard</Link>{" | "}
      <Link to="/client/profile">Profile</Link>{" | "}
      <Link to="/client/photos">Photos</Link>
    </nav>
  );
}
