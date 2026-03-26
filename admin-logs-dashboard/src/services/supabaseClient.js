import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://msyljqazsndtxpritfwy.supabase.co';
const supabaseAnonKey = 'sb_publishable_HXoFqNveyeQcaFrL8suM1A_UBvL2rpZ';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
