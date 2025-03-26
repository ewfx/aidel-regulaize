import React from 'react';
import { FileUpload } from './components/FileUpload';
import { EntitySearch } from './components/EntitySearch';
import { RiskDashboard } from './components/RiskDashboard';
import { FileIcon, SearchIcon, BarChart3Icon } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = React.useState<'upload' | 'search' | 'dashboard'>('upload');

  return (
    <div className="min-h-screen bg-wf-gray-light">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <BarChart3Icon className="h-8 w-8 text-wf-red" />
                <span className="ml-2 text-xl font-bold text-wf-black">360° Risk View Lens</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`${
                    activeTab === 'upload'
                      ? 'border-wf-red text-wf-black'
                      : 'border-transparent text-wf-gray hover:border-wf-gold hover:text-wf-black'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  <FileIcon className="h-4 w-4 mr-2" />
                  File Upload
                </button>
                <button
                  onClick={() => setActiveTab('search')}
                  className={`${
                    activeTab === 'search'
                      ? 'border-wf-red text-wf-black'
                      : 'border-transparent text-wf-gray hover:border-wf-gold hover:text-wf-black'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  <SearchIcon className="h-4 w-4 mr-2" />
                  Entity Search
                </button>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`${
                    activeTab === 'dashboard'
                      ? 'border-wf-red text-wf-black'
                      : 'border-transparent text-wf-gray hover:border-wf-gold hover:text-wf-black'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  <BarChart3Icon className="h-4 w-4 mr-2" />
                  Risk Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' && <FileUpload />}
        {activeTab === 'search' && <EntitySearch />}
        {activeTab === 'dashboard' && <RiskDashboard />}
      </main>
    </div>
  );
}

export default App;