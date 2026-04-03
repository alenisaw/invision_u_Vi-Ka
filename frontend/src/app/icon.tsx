import { ImageResponse } from "next/og";

export const size = {
  width: 64,
  height: 64,
};

export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            "radial-gradient(circle at 25% 20%, rgba(183,223,45,0.35), transparent 48%), linear-gradient(135deg, #0f1614 0%, #15201d 100%)",
        }}
      >
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 18,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(135deg, #b7df2d 0%, #4fd6df 100%)",
            color: "#0f1211",
            fontSize: 22,
            fontWeight: 800,
            boxShadow: "0 10px 24px rgba(0,0,0,0.25)",
          }}
        >
          AI
        </div>
      </div>
    ),
    size,
  );
}
