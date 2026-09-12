import { Pool } from "pg";
import { env } from "./env";
let pool: Pool | undefined;
export const db = () => pool ??= new Pool({ connectionString: env.databaseUrl(), ssl: { rejectUnauthorized: true } });
export const query = (text:string, values:unknown[] = []) => db().query(text, values);
