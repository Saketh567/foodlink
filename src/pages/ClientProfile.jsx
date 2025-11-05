import { useEffect } from "react";
import { useForm } from "react-hook-form";
import api from "../api/axios";

export default function ClientProfile() {
  const { register, handleSubmit, reset } = useForm();

  useEffect(() => {
    api.get("/client/profile").then((res) => reset(res.data || {}));
  }, [reset]);

  const onSubmit = async (values) => {
    await api.put("/client/profile", values);
    alert("Saved!");
  };

  return (
    <div className="container">
      {/* flat wrapper (no card styles here) */}
      <div className="profile-page">
        <h2>Edit Profile</h2>

        <form className="profile-form" onSubmit={handleSubmit(onSubmit)}>
          <div className="field">
            <label>Name</label>
            <input type="text" {...register("name")} />
          </div>

          <div className="field">
            <label>Email</label>
            <input type="email" {...register("email")} />
          </div>

          <div className="field">
            <label>Phone</label>
            <input type="text" {...register("phone")} />
          </div>

          <div className="field">
            <label>Address 1</label>
            <input type="text" {...register("address1")} />
          </div>

          <div className="field">
            <label>Address 2</label>
            <input type="text" {...register("address2")} />
          </div>

          <div className="field two-col">
            <div>
              <label>City</label>
              <input type="text" {...register("city")} />
            </div>
            <div>
              <label>Province/State</label>
              <input type="text" {...register("province")} />
            </div>
          </div>

          <div className="field two-col">
            <div>
              <label>Postal Code</label>
              <input type="text" {...register("postal")} />
            </div>
            <div>
              <label>Family Size</label>
              <input
                type="number"
                {...register("family_size", { valueAsNumber: true })}
              />
            </div>
          </div>

          <div className="field">
            <label>Avg Monthly Income ($)</label>
            <input
              type="number"
              step="0.01"
              {...register("avg_income", { valueAsNumber: true })}
            />
          </div>

          <button className="btn primary" type="submit">
            Save
          </button>
        </form>
      </div>
    </div>
  );
}
