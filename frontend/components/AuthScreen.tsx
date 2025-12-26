import React, { useState } from 'react';
import { User, Lock, Mail, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const AuthScreen: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const { login, register } = useAuth();
  
  // Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, username, password);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#0f0a08] overflow-hidden relative">
      {/* Background Ambience (Warm) */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-orange-600 rounded-full mix-blend-screen filter blur-[120px] opacity-20 animate-pulse"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-amber-700 rounded-full mix-blend-screen filter blur-[120px] opacity-10"></div>
      
      {/* 3D Flip Container */}
      <div className="w-[380px] h-[480px] perspective-[1000px] relative">
        <div className={`relative w-full h-full transition-transform duration-700 transform-style-3d ${!isLogin ? 'rotate-y-180' : ''}`}>
          
          {/* ================= LOGIN CARD (FRONT) ================= */}
          <div className="absolute w-full h-full backface-hidden bg-[#1a120f]/80 backdrop-blur-xl border border-orange-500/30 rounded-2xl shadow-[0_0_40px_rgba(234,88,12,0.15)] p-8 flex flex-col items-center justify-center">
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-orange-500 to-transparent opacity-50"></div>
             
             <h2 className="text-3xl font-bold text-white mb-2 tracking-wider drop-shadow-[0_0_10px_rgba(234,88,12,0.5)]">Login</h2>
             <p className="text-orange-400 text-sm mb-8 tracking-widest uppercase">Welcome Back</p>

             <form onSubmit={handleSubmit} className="w-full space-y-5">
               <div className="relative group">
                 <User className="absolute left-3 top-1/2 -translate-y-1/2 text-orange-500 transition-colors group-focus-within:text-white" size={18} />
                 <input 
                    type="email" 
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-black/40 border border-orange-900/40 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-500 outline-none focus:border-orange-500 focus:shadow-[0_0_15px_rgba(234,88,12,0.2)] transition-all"
                 />
               </div>
               
               <div className="relative group">
                 <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-orange-500 transition-colors group-focus-within:text-white" size={18} />
                 <input 
                    type="password" 
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-black/40 border border-orange-900/40 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-500 outline-none focus:border-orange-500 focus:shadow-[0_0_15px_rgba(234,88,12,0.2)] transition-all"
                 />
               </div>

               {error && <p className="text-red-400 text-xs text-center">{error}</p>}

               <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-orange-600/10 border border-orange-500/50 hover:bg-orange-500 hover:text-white text-orange-500 font-bold py-3 rounded-lg transition-all duration-300 shadow-[0_0_10px_rgba(234,88,12,0.1)] hover:shadow-[0_0_20px_rgba(234,88,12,0.4)] flex items-center justify-center gap-2"
               >
                 {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : 'LOGIN'}
               </button>
             </form>

             <div className="mt-8 text-sm text-gray-400">
               Don't have an account?{' '}
               <button onClick={() => setIsLogin(false)} className="text-orange-400 hover:text-white underline decoration-orange-500 underline-offset-4 transition-colors">
                 Sign Up
               </button>
             </div>
          </div>

          {/* ================= REGISTER CARD (BACK) ================= */}
          <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-[#1a120f]/80 backdrop-blur-xl border border-orange-500/30 rounded-2xl shadow-[0_0_40px_rgba(234,88,12,0.15)] p-8 flex flex-col items-center justify-center">
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-orange-500 to-transparent opacity-50"></div>

             <h2 className="text-3xl font-bold text-white mb-2 tracking-wider drop-shadow-[0_0_10px_rgba(234,88,12,0.5)]">Register</h2>
             <p className="text-orange-400 text-sm mb-6 tracking-widest uppercase">Join the Future</p>

             <form onSubmit={handleSubmit} className="w-full space-y-4">
               <div className="relative group">
                 <User className="absolute left-3 top-1/2 -translate-y-1/2 text-orange-500 transition-colors group-focus-within:text-white" size={18} />
                 <input 
                    type="text" 
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-black/40 border border-orange-900/40 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-500 outline-none focus:border-orange-500 focus:shadow-[0_0_15px_rgba(234,88,12,0.2)] transition-all"
                 />
               </div>

               <div className="relative group">
                 <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-orange-500 transition-colors group-focus-within:text-white" size={18} />
                 <input 
                    type="email" 
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-black/40 border border-orange-900/40 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-500 outline-none focus:border-orange-500 focus:shadow-[0_0_15px_rgba(234,88,12,0.2)] transition-all"
                 />
               </div>
               
               <div className="relative group">
                 <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-orange-500 transition-colors group-focus-within:text-white" size={18} />
                 <input 
                    type="password" 
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-black/40 border border-orange-900/40 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-500 outline-none focus:border-orange-500 focus:shadow-[0_0_15px_rgba(234,88,12,0.2)] transition-all"
                 />
               </div>

               {error && <p className="text-red-400 text-xs text-center">{error}</p>}

               <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-orange-600/10 border border-orange-500/50 hover:bg-orange-500 hover:text-white text-orange-500 font-bold py-3 rounded-lg transition-all duration-300 shadow-[0_0_10px_rgba(234,88,12,0.1)] hover:shadow-[0_0_20px_rgba(234,88,12,0.4)] flex items-center justify-center gap-2"
               >
                 {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : 'SIGN UP'}
               </button>
             </form>

             <div className="mt-6 text-sm text-gray-400">
               Already have an account?{' '}
               <button onClick={() => setIsLogin(true)} className="text-orange-400 hover:text-white underline decoration-orange-500 underline-offset-4 transition-colors">
                 Sign In
               </button>
             </div>
          </div>

        </div>
      </div>
      
      <style>{`
        .perspective-\\[1000px\\] {
          perspective: 1000px;
        }
        .transform-style-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
      `}</style>
    </div>
  );
};

export default AuthScreen;