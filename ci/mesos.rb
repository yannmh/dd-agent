require './ci/common'

def mesos_rootdir
  "#{ENV['INTEGRATIONS_DIR']}/mesos"
end

namespace :ci do
  namespace :mesos do |flavor|
    task :before_install => ['ci:common:before_install']

    task :install => ['ci:common:install'] do
      unless Dir.exist? File.expand_path(mesos_rootdir)
        sh %(curl -s -L\
             -o $VOLATILE_DIR/mesos-0.22.0.tar.gz \
             https://s3.amazonaws.com/dd-agent-tarball-mirror/mesos-0.22.0.tar.gz)
        sh %(mkdir -p $VOLATILE_DIR/mesos/build)
        sh %(tar zxf $VOLATILE_DIR/mesos-0.22.0.tar.gz \
             -C $VOLATILE_DIR/mesos --strip-components=1)
        sh %(mkdir -p #{mesos_rootdir})
        sh %(cd $VOLATILE_DIR/mesos/build\
             && ../configure --prefix=#{mesos_rootdir} \
             && make -j $CONCURRENCY\
             && make install)
      end
    end

    task :before_script => ['ci:common:before_script'] do

    end

    task :script => ['ci:common:script'] do
      this_provides = [
        'mesos'
      ]
      Rake::Task['ci:common:run_tests'].invoke(this_provides)
    end

    task :before_cache => ['ci:common:before_cache']

    task :cache => ['ci:common:cache']

    task :cleanup => ['ci:common:cleanup'] do
      sh %(rm -r $VOLATILE_DIR/mesos*)
    end

    task :execute do
      exception = nil
      begin
        %w(before_install install before_script script).each do |t|
          Rake::Task["#{flavor.scope.path}:#{t}"].invoke
        end
      rescue => e
        exception = e
        puts "Failed task: #{e.class} #{e.message}".red
      end
      if ENV['SKIP_CLEANUP']
        puts 'Skipping cleanup, disposable environments are great'.yellow
      else
        puts 'Cleaning up'
        Rake::Task["#{flavor.scope.path}:cleanup"].invoke
      end
      if ENV['TRAVIS']
        %w(before_cache cache).each do |t|
          Rake::Task["#{flavor.scope.path}:#{t}"].invoke
        end
      end
      fail exception if exception
    end
  end
end
