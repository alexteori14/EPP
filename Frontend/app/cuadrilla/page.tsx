import { getHallazgosData } from '@/lib/data/loader';
import { CuadrillaView } from '@/components/cuadrilla/CuadrillaView';

export const dynamic = 'force-dynamic';

export default async function CuadrillaPage({
  searchParams,
}: {
  searchParams: Promise<{ pos?: string }>;
}) {
  const [data, params] = await Promise.all([getHallazgosData(), searchParams]);
  return <CuadrillaView data={data} posicionInicial={params?.pos} />;
}
