import React from 'react';
import { FaSearch } from 'react-icons/fa';
import { InstitutionData } from './types';
import { InstitutionCard } from './ui-components';
import ChoroplethMap from '@/components/map';

interface InstitutionsTabProps {
    filteredInstitutions: InstitutionData[];
    institutionFilter: string;
    setInstitutionFilter: (filter: string) => void;
}

const InstitutionsTab: React.FC<InstitutionsTabProps> = ({
    filteredInstitutions,
    institutionFilter,
    setInstitutionFilter
}) => {
    // Dummy data for the map (replace with real data as needed)
    const indiaInstitutionsMapData = filteredInstitutions.map(inst => ({
        country: 'India',
        iso_code: 'IND',
        author_count: inst.author_count,
        institute: inst.institute,
    }));

    return (
        <div className="space-y-6 md:space-y-8 animate-fade-in">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div>
                    <h2 className="text-xl font-semibold text-foreground">Indian Institutions</h2>
                    <p className="text-sm text-muted-foreground">View detailed information about contributing Indian institutions.</p>
                </div>
                <div className="relative w-full sm:w-64">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-muted-foreground">
                        <FaSearch size={14} />
                    </div>
                    <input
                        type="text"
                        value={institutionFilter}
                        onChange={(e) => setInstitutionFilter(e.target.value)}
                        className="bg-muted/30 border border-border text-foreground text-sm rounded-lg block w-full pl-10 p-2.5 focus:ring-2 focus:ring-primary/50 focus:border-primary/50"
                        placeholder="Search institutions..."
                    />
                </div>
            </div>

            {/* Responsive 2-column layout for desktop, stack on mobile */}
            <div className="flex flex-col lg:flex-row gap-8">
                {/* Left: Bar charts (replace with your actual chart components) */}
                <div className="flex-1 flex flex-col gap-6 min-w-0">
                    {/* Example horizontal bar chart placeholder */}
                    {/* <YourBarChartComponent1 data={...} /> */}
                    {/* <YourBarChartComponent2 data={...} /> */}
                    <div className="bg-muted/30 rounded-lg p-4 text-center text-muted-foreground">[Bar Chart 1 Placeholder]</div>
                    <div className="bg-muted/30 rounded-lg p-4 text-center text-muted-foreground">[Bar Chart 2 Placeholder]</div>
                </div>
                {/* Right: India map with institutions highlighted */}
                <div className="flex-1 min-w-0">
                    <div className="bg-muted/30 rounded-lg p-4 h-[400px]">
                        <ChoroplethMap data={indiaInstitutionsMapData} title="Indian Institutions Map" />
                    </div>
                </div>
            </div>

            {/* Institution cards grid below charts/map */}
            {filteredInstitutions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    <div className="text-lg font-medium">No institutions found</div>
                    <p className="text-sm mt-2">Try adjusting your search criteria</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6 mt-8">
                    {filteredInstitutions.map((institution, index) => (
                        <InstitutionCard key={institution.institute} institution={institution} index={index} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default InstitutionsTab;
