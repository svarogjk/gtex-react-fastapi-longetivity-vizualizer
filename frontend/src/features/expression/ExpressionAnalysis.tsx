import { GeneSelector } from './GeneSelector';
import { TissueSelector } from './TissueSelector';
import { DatasetSelector } from './DatasetSelector'; 
import { TissueExpressionChart } from './TissueExpressionChart';
import { DatasetMetadataTable } from './DatasetMetadataTable'; 
import { useAppSelector } from '../../app/hooks';

export const ExpressionAnalysis = () => {
  // Get selected gene from Redux store
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  const selectedTissue = useAppSelector(state => state.expression.selectedTissue);
  const selectedDataset = useAppSelector(state => state.expression.selectedDataset);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Gene Expression Analysis</h1>
      
      <div className="space-y-6">
        <GeneSelector />
        
        {selectedGene && (
          <>
            <TissueExpressionChart />
            <TissueSelector />

            {selectedTissue && (
              <>
                <DatasetSelector />
                {selectedDataset && (
                  <DatasetMetadataTable />
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};