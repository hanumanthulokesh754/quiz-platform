from supabase import create_client, Client
from config import Config

_supabase: Client | None = None


def get_supabase() -> Client:
    """Returns a singleton Supabase client using the service-role key.

    All Supabase access happens server-side through this client, so
    table RLS policies can stay deny-all for anon/public roles.
    """
    global _supabase
    if _supabase is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY are not set. Copy .env.example to .env and fill them in."
            )
        _supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    return _supabase
