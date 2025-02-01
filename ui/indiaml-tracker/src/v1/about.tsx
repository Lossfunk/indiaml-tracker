import React from 'react';

const AboutSection = () => {
  return (
    <section className="bg-gray-100 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 dark:text-gray-100">
            Indian Contributions to Machine Learning
          </h2>
          <p className="mt-4 text-xl text-gray-600 dark:text-gray-300">
            Celebrating groundbreaking research and innovation at premier conferences like ICML, NeurIPS, AAAI, and more.
          </p>
        </div>

        {/* Mission Section */}
        <div className="mb-12">
          <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
            Our Mission
          </h3>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Our goal is to showcase the tremendous work and dedication of Indian researchers in the field of Machine Learning and Artificial Intelligence. We aim to inspire future generations, foster collaboration, and drive technological advancements through innovative research.
            The whole analytics and data processing pipeline is based on OpenReview and the code is publicly available.
          </p>
        </div>
        {/* Call to Action */}
        <div className="my-10">
          <a
            href="https://github.com/ronniebasak/indiaml-tracker/"
            className="inline-block bg-gray-800 dark:bg-gray-100 text-white dark:text-gray-900 font-semibold py-3 px-6 rounded hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors duration-300"
          >
            View on GitHub
          </a>
        </div>


        {/* Achievements Section */}
        <div className="mb-12">
          <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
            Key Achievements
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h4 className="text-xl font-bold text-gray-700 dark:text-gray-200">ICML</h4>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Indian researchers have consistently contributed high-impact papers and innovative models that set new performance benchmarks.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h4 className="text-xl font-bold text-gray-700 dark:text-gray-200">NeurIPS</h4>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                A growing number of groundbreaking studies and keynote presentations have underscored the global influence of Indian contributions.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h4 className="text-xl font-bold text-gray-700 dark:text-gray-200">AAAI</h4>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Recognized for excellence, Indian-led research at AAAI continues to inspire and drive advancements in AI.
              </p>
            </div>
          </div>
        </div>

        {/* Milestones Timeline */}
        <div className="mb-12">
          <h3 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
            Milestones Timeline
          </h3>
          <div className="relative border-l border-gray-300 dark:border-gray-700">
            <div className="mb-6 ml-4">
              <div className="absolute w-3 h-3 bg-blue-500 rounded-full mt-1.5 -left-1.5 border border-white"></div>
              <time className="mb-1 text-sm font-normal text-gray-500 dark:text-gray-400">2015</time>
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Breakthrough in Deep Learning
              </h4>
              <p className="text-base font-normal text-gray-600 dark:text-gray-300">
                Indian teams introduced innovative deep learning models that redefined performance standards.
              </p>
            </div>
            <div className="mb-6 ml-4">
              <div className="absolute w-3 h-3 bg-blue-500 rounded-full mt-1.5 -left-1.5 border border-white"></div>
              <time className="mb-1 text-sm font-normal text-gray-500 dark:text-gray-400">2017</time>
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Landmark Contributions at ICML
              </h4>
              <p className="text-base font-normal text-gray-600 dark:text-gray-300">
                Award-winning research and novel contributions from Indian scholars captured global attention at ICML.
              </p>
            </div>
            <div className="mb-6 ml-4">
              <div className="absolute w-3 h-3 bg-blue-500 rounded-full mt-1.5 -left-1.5 border border-white"></div>
              <time className="mb-1 text-sm font-normal text-gray-500 dark:text-gray-400">2019</time>
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Innovations at NeurIPS
              </h4>
              <p className="text-base font-normal text-gray-600 dark:text-gray-300">
                A surge in pioneering research at NeurIPS further established India's role in shaping the future of ML.
              </p>
            </div>
            <div className="mb-6 ml-4">
              <div className="absolute w-3 h-3 bg-blue-500 rounded-full mt-1.5 -left-1.5 border border-white"></div>
              <time className="mb-1 text-sm font-normal text-gray-500 dark:text-gray-400">2024</time>
              <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                Project Initiation
              </h4>
              <p className="text-base font-normal text-gray-600 dark:text-gray-300">
                This project started in 2024, building on previous milestones to document the evolving landscape of deep learning.
              </p>
            </div>
          </div>
        </div>


      </div>
    </section>
  );
};

export default AboutSection;
