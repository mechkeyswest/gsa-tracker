import React, { useState } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { 
  ShieldAlert, Calendar, BookOpen, CheckCircle2, 
  Circle, ChevronRight, LayoutDashboard, Settings 
} from 'lucide-react';

// --- CONFIG & THEME ---
const SUPER_ADMIN = "armasupplyguy@gmail.com";

const App = () => {
  const [currentUser] = useState({ email: "armasupplyguy@gmail.com", role: "SUPER_ADMIN" });
  const [activeTab, setActiveTab] = useState('broken-mods');
  
  // --- STATE FOR DATA ---
  const [mods, setMods] = useState([
    { id: 1, name: "ACE Medical Bug", photo: "", severity: 8, assigned: "John Doe", completed: false, description: "" }
  ]);

  const [events, setEvents] = useState([]);
  
  // --- CALCULATE SIDEBAR LIGHT ---
  const modStatusColor = mods.some(m => !m.completed) ? "text-red-500" : "text-green-500";

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      {/* SIDEBAR */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col">
        <div className="p-6 font-bold text-xl tracking-tight border-b border-slate-800">
          STAFF PORTAL
        </div>
        
        <nav className="flex-1 p-4 space-y-8">
          {/* SERVER ADMIN CATEGORY */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-4 px-2">Server Admin</h3>
            <button 
              onClick={() => setActiveTab('broken-mods')}
              className={`flex items-center w-full p-2 rounded transition ${activeTab === 'broken-mods' ? 'bg-slate-800 text-white' : 'hover:bg-slate-900 text-slate-400'}`}
            >
              <div className={`mr-3 ${modStatusColor}`}>
                <Circle size={12} fill="currentColor" />
              </div>
              Broken Mods
            </button>
          </div>

          {/* CLP LEAD CATEGORY */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-4 px-2">CLP LEAD</h3>
            <div className="space-y-1">
              <button 
                onClick={() => setActiveTab('events')}
                className={`flex items-center w-full p-2 rounded transition ${activeTab === 'events' ? 'bg-slate-800 text-white' : 'hover:bg-slate-900 text-slate-400'}`}
              >
                <Calendar size={18} className="mr-3" /> Events
              </button>
              <button 
                onClick={() => setActiveTab('tutorials')}
                className={`flex items-center w-full p-2 rounded transition ${activeTab === 'tutorials' ? 'bg-slate-800 text-white' : 'hover:bg-slate-900 text-slate-400'}`}
              >
                <BookOpen size={18} className="mr-3" /> Tutorials
              </button>
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
          Logged in as: <br/> <span className="text-slate-300">{currentUser.email}</span>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto p-8">
        {activeTab === 'broken-mods' && <BrokenModsView mods={mods} setMods={setMods} />}
        {activeTab === 'events' && <EventsView events={events} setEvents={setEvents} />}
        {activeTab === 'tutorials' && <TutorialsView />}
      </main>
    </div>
  );
};

// --- SUB-COMPONENTS ---

const BrokenModsView = ({ mods, setMods }) => {
  const addMod = () => {
    const newMod = { id: Date.now(), name: "", severity: 1, completed: false, description: "" };
    setMods([...mods, newMod]);
  };

  const updateMod = (id, field, value) => {
    setMods(mods.map(m => m.id === id ? { ...m, [field]: value } : m));
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold">Broken Mods List</h2>
        <button onClick={addMod} className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded">Add Mod Task</button>
      </div>

      <div className="space-y-6">
        {mods.map(mod => (
          <div key={mod.id} className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Mod Name</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-900 border border-slate-700 p-2 rounded"
                  value={mod.name}
                  onChange={(e) => updateMod(mod.id, 'name', e.target.value)}
                />
              </div>
              <div className="flex items-end space-x-4">
                <div className="flex-1">
                  <label className="block text-sm text-slate-400 mb-1">Severity (1-10): {mod.severity}</label>
                  <input 
                    type="range" min="1" max="10" 
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                    value={mod.severity}
                    onChange={(e) => updateMod(mod.id, 'severity', e.target.value)}
                  />
                </div>
                <div className="flex items-center">
                   <input 
                    type="checkbox" 
                    className="w-6 h-6 rounded border-slate-700 bg-slate-900 text-green-500 focus:ring-0"
                    checked={mod.completed}
                    onChange={(e) => updateMod(mod.id, 'completed', e.target.checked)}
                   />
                   <span className="ml-2 text-sm text-slate-400">Complete</span>
                </div>
              </div>
            </div>

            <label className="block text-sm text-slate-400 mb-2">Detailed Notes (Rich Text)</label>
            <div className="bg-white text-black rounded">
              <ReactQuill theme="snow" value={mod.description} onChange={(val) => updateMod(mod.id, 'description', val)} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const EventsView = ({ events, setEvents }) => {
  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold mb-8">CLP Events Calendar</h2>
      <div className="bg-slate-800 p-8 rounded-xl border border-dashed border-slate-600 text-center">
        <p className="text-slate-400 mb-4">Event Creation Form for CLP LEADS</p>
        <div className="grid grid-cols-2 gap-4 text-left">
           <input placeholder="Event Name" className="bg-slate-900 p-2 border border-slate-700 rounded"/>
           <input type="datetime-local" className="bg-slate-900 p-2 border border-slate-700 rounded text-white"/>
           <select className="bg-slate-900 p-2 border border-slate-700 rounded">
             <option>EST</option><option>GMT</option><option>PST</option>
           </select>
           <input placeholder="Location (Server IP/Discord)" className="bg-slate-900 p-2 border border-slate-700 rounded"/>
        </div>
        <div className="mt-4 bg-white text-black rounded text-left">
           <ReactQuill placeholder="Event Description..." />
        </div>
      </div>
    </div>
  );
};

const TutorialsView = () => (
  <div className="max-w-4xl mx-auto">
    <h2 className="text-3xl font-bold mb-8">Tutorials</h2>
    <div className="bg-white text-black rounded min-h-[400px]">
       <ReactQuill theme="snow" placeholder="Write your tutorial here..." />
    </div>
  </div>
);

export default App;
