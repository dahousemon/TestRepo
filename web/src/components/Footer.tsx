import Link from 'next/link';

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🏔️</span>
              <span className="font-bold text-xl text-white">
                Colorado <span className="text-blue-400">200</span>
              </span>
            </div>
            <p className="text-sm">
              Explore Colorado&apos;s 200 highest peaks. Track your summits and plan your next adventure.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Explore</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/" className="hover:text-white transition-colors">All Peaks</Link></li>
              <li><Link href="/map" className="hover:text-white transition-colors">Interactive Map</Link></li>
              <li><Link href="/?category=fourteener" className="hover:text-white transition-colors">Fourteeners</Link></li>
              <li><Link href="/?category=thirteener" className="hover:text-white transition-colors">Thirteeners</Link></li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-white font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li><a href="https://14ers.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">14ers.com</a></li>
              <li><a href="https://www.alltrails.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">AllTrails</a></li>
              <li><a href="https://www.weather.gov" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Weather.gov</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
          <p>© {new Date().getFullYear()} Colorado 200. Data sourced from USGS and public records.</p>
          <p className="mt-2">Always check conditions before climbing. Safety first.</p>
        </div>
      </div>
    </footer>
  );
}
