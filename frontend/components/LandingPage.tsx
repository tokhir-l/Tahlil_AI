
import React, { useEffect, useState } from 'react';
import { ArrowRight, BarChart2, Database, FileText, Lock, UploadCloud, Zap } from 'lucide-react';
import ParticleBackground from './ParticleBackground';

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#0f0a08] text-white overflow-x-hidden font-sans selection:bg-orange-500/30">
      
      {/* Navbar */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrollY > 50 ? 'bg-[#0f0a08]/80 backdrop-blur-md border-b border-white/5' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-orange-500 to-amber-600 rounded-lg flex items-center justify-center shadow-lg shadow-orange-500/20">
              <span className="font-bold text-white text-lg">T</span>
            </div>
            <span className="text-xl font-bold tracking-tight">Tahlil<span className="text-orange-500">.ai</span></span>
          </div>
          <button 
            onClick={onGetStarted}
            className="px-5 py-2.5 rounded-full border border-white/10 hover:bg-white/5 hover:border-orange-500/50 transition-all text-sm font-medium"
          >
            Log In
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-12 px-6 overflow-hidden">
        {/* Particle Background */}
        <ParticleBackground />

        {/* Background Ambience - Balanced */}
        <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-orange-600/10 rounded-full blur-[120px] -z-10 animate-pulse-slow pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[600px] h-[600px] bg-amber-800/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>

        <div className="max-w-5xl w-full mx-auto text-center relative z-10 flex flex-col items-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-medium mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Zap size={12} className="fill-current" />
            <span>Now with Gemini 3 Pro Support</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight leading-tight animate-in fade-in slide-in-from-bottom-8 duration-700 delay-100">
            Your Personal AI <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-amber-600">Data Scientist</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
            Upload CSVs, Excel, or Parquet files. Tahlil analyzes your data, uncovers hidden trends, and generates visualization code instantly.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300 w-full">
            <button 
              onClick={onGetStarted}
              className="px-8 py-4 bg-orange-600 hover:bg-orange-500 text-white rounded-full font-semibold text-lg transition-all shadow-lg shadow-orange-600/20 hover:shadow-orange-600/40 flex items-center justify-center gap-2 group w-full sm:w-auto"
            >
              Start Analyzing Now
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <a 
              href="#features"
              className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-full font-medium text-lg transition-all flex items-center justify-center w-full sm:w-auto"
            >
              Learn More
            </a>
          </div>

          {/* Abstract Interface Preview - Centered Below */}
          <div className="mt-16 w-full max-w-4xl mx-auto animate-in fade-in zoom-in-95 duration-1000 delay-500 z-10 hidden md:block">
            <div className="relative">
               <div className="absolute -inset-1 bg-gradient-to-r from-orange-500 to-amber-600 rounded-2xl blur opacity-20"></div>
               <div className="relative bg-[#1a120f] border border-white/10 rounded-2xl aspect-[16/9] shadow-2xl overflow-hidden flex flex-col">
                  {/* Fake Browser Header */}
                  <div className="h-10 bg-white/5 border-b border-white/5 flex items-center px-4 gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/20"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/20"></div>
                  </div>
                  {/* Fake Content */}
                  <div className="flex-1 flex">
                    <div className="w-16 border-r border-white/5 bg-white/[0.02]"></div>
                    <div className="flex-1 p-8 grid grid-cols-2 gap-8">
                       <div className="space-y-4">
                          <div className="h-8 w-3/4 bg-white/10 rounded-lg animate-pulse"></div>
                          <div className="h-4 w-1/2 bg-white/5 rounded-lg animate-pulse"></div>
                          <div className="h-4 w-full bg-white/5 rounded-lg animate-pulse delay-75"></div>
                          <div className="h-4 w-5/6 bg-white/5 rounded-lg animate-pulse delay-150"></div>
                       </div>
                       <div className="bg-white/5 rounded-xl border border-white/5 p-4 flex items-end justify-between gap-2">
                          <div className="w-full bg-orange-500/20 rounded-t h-[40%]"></div>
                          <div className="w-full bg-orange-500/40 rounded-t h-[70%]"></div>
                          <div className="w-full bg-orange-500/60 rounded-t h-[50%]"></div>
                          <div className="w-full bg-orange-500/80 rounded-t h-[90%]"></div>
                       </div>
                    </div>
                  </div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 bg-[#0f0a08]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Tahlil?</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Built for data-driven decisions without the coding complexity.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<UploadCloud size={32} className="text-orange-500" />}
              title="File-First Analysis"
              description="Simply drag and drop your CSV, Excel, or Parquet files. We handle the parsing and cleaning."
            />
            <FeatureCard 
              icon={<BarChart2 size={32} className="text-amber-500" />}
              title="Instant Visualizations"
              description="Ask for a chart, and get a generated Python/Plotly visualization instantly."
            />
            <FeatureCard 
              icon={<Database size={32} className="text-red-500" />}
              title="Secure Storage"
              description="Your data is stored securely and automatically cleared after 30 days to ensure privacy."
            />
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-white/[0.02]"></div>
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">From Raw Data to <br />Insight in Seconds</h2>
              <div className="space-y-8">
                <Step 
                  number="01" 
                  title="Upload Data" 
                  description="Securely upload your dataset. We support large files up to 100MB." 
                />
                <Step 
                  number="02" 
                  title="Ask Questions" 
                  description="Use natural language. 'Show me sales trends for Q3' or 'Identify outliers'." 
                />
                <Step 
                  number="03" 
                  title="Get Results" 
                  description="Receive comprehensive analysis, code snippets, and interactive charts." 
                />
              </div>
              <div className="mt-10">
                <button 
                  onClick={onGetStarted}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg font-medium transition-all"
                >
                  Get Started for Free
                </button>
              </div>
            </div>
            <div className="relative">
               {/* Decorative Circles */}
               <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-gradient-to-br from-orange-500/20 to-transparent rounded-full blur-3xl"></div>
               <div className="relative bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
                 <div className="flex items-center gap-4 mb-4">
                   <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-500">
                     <FileText size={20} />
                   </div>
                   <div>
                     <div className="text-sm font-medium text-white">sales_data_2024.csv</div>
                     <div className="text-xs text-gray-500">12.5 MB • Uploaded just now</div>
                   </div>
                 </div>
                 <div className="space-y-3">
                   <div className="h-2 bg-white/10 rounded w-full"></div>
                   <div className="h-2 bg-white/10 rounded w-5/6"></div>
                   <div className="h-2 bg-white/10 rounded w-4/6"></div>
                 </div>
                 <div className="mt-6 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                   <p className="text-orange-200 text-sm">"I found a 15% increase in churn rate for users in the basic tier. Here is a breakdown..."</p>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5 bg-[#0a0706] text-center">
        <div className="flex items-center justify-center gap-2 mb-6 opacity-50">
          <div className="w-6 h-6 bg-gray-700 rounded-lg flex items-center justify-center">
            <span className="font-bold text-white text-xs">T</span>
          </div>
          <span className="font-bold tracking-tight">Tahlil.ai</span>
        </div>
        <p className="text-gray-600 text-sm">© 2024 Tahlil AI. All rights reserved.</p>
      </footer>
    </div>
  );
};

const FeatureCard: React.FC<{ icon: React.ReactNode, title: string, description: string }> = ({ icon, title, description }) => (
  <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] hover:border-orange-500/30 transition-all group">
    <div className="mb-4 p-3 bg-white/5 rounded-xl w-fit group-hover:scale-110 transition-transform duration-300">
      {icon}
    </div>
    <h3 className="text-xl font-bold mb-2 text-white">{title}</h3>
    <p className="text-gray-400 leading-relaxed">{description}</p>
  </div>
);

const Step: React.FC<{ number: string, title: string, description: string }> = ({ number, title, description }) => (
  <div className="flex gap-4">
    <div className="text-orange-500 font-mono font-bold text-lg pt-1 opacity-50">{number}</div>
    <div>
      <h3 className="text-xl font-bold mb-1 text-white">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </div>
  </div>
);

export default LandingPage;
