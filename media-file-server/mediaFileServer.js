import express from "express";
import path from "path";

const app = express();
app.use("/images", express.static(path.join(process.cwd(), "images")));

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server is running on Port: ${PORT}`);
});