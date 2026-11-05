import { getHallazgosData } from '@/lib/data/loader';
import { AsistenteView } from '@/components/asistente/AsistenteView';

export const dynamic = 'force-dynamic';

export default async function AsistentePage() {
  const data = await getHallazgosData();
  return <AsistenteView data={data} />;
}
