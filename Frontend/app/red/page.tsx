import { getRedData } from '@/lib/data/loader';
import { RedView } from '@/components/red/RedView';

export const dynamic = 'force-dynamic';

export default async function RedPage() {
  const data = await getRedData();
  return <RedView data={data} />;
}
