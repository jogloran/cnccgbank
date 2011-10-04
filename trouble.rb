#! /usr/bin/env ruby
phases = ARGV.empty? ? %w{tagged binarised labelled fixed_rc fixed_adverbs fixed_np} : ARGV

STDIN.each_with_index {|line, i|
    if i != 0 and i % 10 == 0
        STDOUT.write "Continue? "
        case gets
        when "n"
            exit
        end
    end
        
    line.chomp!
    
    (line =~ /(\d+):(\d+)\((\d+)\)/) || (line =~ /(\d+),(\d+),(\d+)/) || (line =~ /(\d{1,2}).*?(\d{1,2}).*?(\d+)/)
    sec, doc, deriv = $1.to_i, $2.to_i, $3.to_i
    doc_name = "chtb_%02d%02d.fid" % [sec, doc]
    pdf_name = "wsj_%02d%02d.%02d.pdf" % [sec, doc, deriv]
    section_name = "%02d" % sec
    
    puts "Making %d:%d(%d)..." % [sec, doc, deriv]
    `./make_all.sh #{doc_name}:#{$3}`
    phases.each {|phase|
        if ["tagged", "binarised"].include? phase
            `./t -q -D #{phase}_dots #{phase}/#{doc_name}:#{$3} 2>&1`
        else
            `./t -q -D #{phase}_dots -R PrefacedPTBReader #{phase}/#{doc_name}:#{$3} 2>&1`
        end
    }
    open_cmd = "open -a /Applications/Preview.app "
    dot_files = phases.map {|phase| "#{phase}_dots/#{section_name}/#{pdf_name}"}.select {|file| test ?f, file}
    open_cmd += dot_files.join(' ')
    puts open_cmd
    system open_cmd
}
