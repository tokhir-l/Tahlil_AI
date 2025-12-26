
import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Dashboard } from '../types';

const DashboardGallery: React.FC = () => {
    const [dashboards, setDashboards] = useState<Dashboard[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadDashboards = async () => {
            try {
                const data = await api.getDashboards();
                setDashboards(data);
            } catch (e) {
                console.error("Failed to load dashboards", e);
            } finally {
                setIsLoading(false);
            }
        };
        loadDashboards();
    }, []);

    const openDashboard = (url: string) => {
        window.open(url, '_blank');
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500">
                <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mr-2"></div>
                Loading dashboards...
            </div>
        );
    }

    if (dashboards.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8">
                <div className="w-16 h-16 bg-secondary rounded-2xl flex items-center justify-center mb-4 text-3xl opacity-50">
                    📊
                </div>
                <h3 className="text-xl font-semibold mb-2">No Dashboards Yet</h3>
                <p className="text-center max-w-md text-sm opacity-80">
                    Ask the AI to "create a dashboard" from your data analysis to see it here.
                </p>
            </div>
        );
    }

    return (
        <div className="p-8 h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 text-foreground">My Dashboards</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashboards.map((dash) => (
                    <div
                        key={dash.id}
                        className="group bg-secondary/30 border border-border rounded-xl overflow-hidden hover:border-orange-500/50 transition-all cursor-pointer hover:shadow-lg hover:shadow-orange-500/5"
                        onClick={() => openDashboard(dash.file_url)}
                    >
                        {/* Thumbnail Placeholder */}
                        <div className="h-40 bg-gradient-to-br from-secondary to-background flex items-center justify-center group-hover:scale-105 transition-transform duration-500">
                            <span className="text-4xl opacity-20">📈</span>
                        </div>

                        <div className="p-4">
                            <h3 className="font-semibold text-foreground mb-1 line-clamp-1 truncate" title={dash.title}>
                                {dash.title}
                            </h3>
                            <div className="flex justify-between items-center text-xs text-muted-foreground mt-2">
                                <span>{new Date(dash.date).toLocaleDateString()}</span>
                                <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-full text-[10px] font-medium">
                                    OPEN
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DashboardGallery;
