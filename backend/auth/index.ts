import { Router } from "express";
import signupRouter from "./signup.js";
import signinRouter from "./signin.js";
import verificationRouter from "./verification.js";
import sessionRouter from "./session.js";
import googleRouter from "./google.js";

const router = Router();

router.use("/signup", signupRouter);
router.use("/signin", signinRouter);
router.use(verificationRouter);   // /verify-email, /resend-verification, /verification-status
router.use(sessionRouter);        // /refresh, /logout, /me
router.use(googleRouter);         // /google, /google/callback

export default router;
